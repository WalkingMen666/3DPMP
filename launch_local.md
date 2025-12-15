podman-compose up -d db redis #or sudo docker compose up -d db redis
source .venv/bin/activate
cd backend
python manage.py runserver
cd ../frontend
npm run dev