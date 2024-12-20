## Project setup guide

Build project image:
```shell
docker compose build
```
This command will create Docker image based on the ```Dockerfile```

Great, now you are ready to launch composition by running:
```shell
docker compose up
```
This command will start the container defined in ```docker-compose.yml```


After launching project, you should apply migrations. Run these commands:
```shell
docker-compose exec backend python3 /application/manage.py makemigrations
docker-compose exec backend python3 /application/manage.py migrate
```

To create a superuser for accessing admin panel, run:
```shell
docker-compose exec backend python3 /application/manage.py createsuperuser
```

Notice: if you modify the project code, you 
__do not need to rebuild the composition__. 
The project directory mounted inside the container,
so changes are automatically applied.

But if you update dependencies, modify ```docker-compose.yml```
or add new static files, you must rebuild the composition:
```shell
docker compose build
```

To stop the running containers, press ```Ctrl+C``` where
```docker compose up``` is running. Also you can stop it via
```shell
docker compose down
```

If you need to check the logs for errors you may use this command:
```shell
docker-compose logs backend
```
