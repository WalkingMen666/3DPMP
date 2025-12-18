"""
Celery tasks for model slicing using PrusaSlicer.
"""
import os
import re
import subprocess
import tempfile
import logging

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def slice_model(self, model_id: str):
    """
    Slice a 3D model STL file using PrusaSlicer.
    
    Extracts filament usage info from the generated G-code comments:
    - ; filament used [mm] = 4479.14
    - ; filament used [cm3] = 10.77
    
    Args:
        model_id: UUID of the Model to slice
    """
    from apps.models.models import Model, SlicingStatus
    
    try:
        model = Model.objects.get(id=model_id)
    except Model.DoesNotExist:
        logger.error(f"Model {model_id} not found")
        return
    
    # Update status to processing
    model.slicing_status = SlicingStatus.PROCESSING
    model.slicing_error = None
    model.save(update_fields=['slicing_status', 'slicing_error'])
    
    try:
        # Get STL file path
        if model.stl_file:
            stl_path = model.stl_file.path
        elif model.stl_file_path:
            stl_path = os.path.join(settings.MEDIA_ROOT, model.stl_file_path)
        else:
            raise ValueError("No STL file available")
        
        if not os.path.exists(stl_path):
            raise FileNotFoundError(f"STL file not found: {stl_path}")
        
        # Create output directory for gcode
        gcode_dir = os.path.join(settings.MEDIA_ROOT, 'models', 'gcode')
        os.makedirs(gcode_dir, exist_ok=True)
        
        # Generate gcode filename
        gcode_filename = f"{model_id}.gcode"
        gcode_path = os.path.join(gcode_dir, gcode_filename)
        
        # Run PrusaSlicer
        cmd = [
            'prusa-slicer',
            '--slice',
            '--export-gcode',
            '-o', gcode_path,
            stl_path
        ]
        
        logger.info(f"Running PrusaSlicer: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"PrusaSlicer failed: {result.stderr}")
        
        # Parse the gcode file for filament usage
        slicing_info = parse_gcode_for_slicing_info(gcode_path)
        slicing_info['gcode_path'] = f"models/gcode/{gcode_filename}"
        slicing_info['source'] = 'auto'
        
        # Update model
        model.slicing_info = slicing_info
        model.gcode_file_path = slicing_info['gcode_path']
        model.slicing_status = SlicingStatus.COMPLETED
        model.slicing_error = None
        model.save(update_fields=['slicing_info', 'gcode_file_path', 'slicing_status', 'slicing_error'])
        
        logger.info(f"Successfully sliced model {model_id}: {slicing_info}")
        
    except Exception as e:
        logger.exception(f"Failed to slice model {model_id}")
        model.slicing_status = SlicingStatus.FAILED
        model.slicing_error = str(e)
        model.save(update_fields=['slicing_status', 'slicing_error'])
        
        # Retry on certain failures
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


def parse_gcode_for_slicing_info(gcode_path: str) -> dict:
    """
    Parse a G-code file to extract slicing information.
    
    Looks for comments like:
    - ; filament used [mm] = 4479.14
    - ; filament used [cm3] = 10.77
    
    Returns:
        dict with filament_used_mm and filament_used_cm3
    """
    slicing_info = {
        'filament_used_mm': None,
        'filament_used_cm3': None,
    }
    
    # Patterns to match
    mm_pattern = re.compile(r';\s*filament used \[mm\]\s*=\s*([\d.]+)')
    cm3_pattern = re.compile(r';\s*filament used \[cm3\]\s*=\s*([\d.]+)')
    
    try:
        with open(gcode_path, 'r') as f:
            for line in f:
                if 'filament used' in line:
                    mm_match = mm_pattern.search(line)
                    if mm_match:
                        slicing_info['filament_used_mm'] = float(mm_match.group(1))
                    
                    cm3_match = cm3_pattern.search(line)
                    if cm3_match:
                        slicing_info['filament_used_cm3'] = float(cm3_match.group(1))
                
                # Stop early if we found both values
                if slicing_info['filament_used_mm'] and slicing_info['filament_used_cm3']:
                    break
    except Exception as e:
        logger.error(f"Error parsing gcode file {gcode_path}: {e}")
    
    return slicing_info
