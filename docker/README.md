# Container Deployment
This scraper can be built and deployed with a Docker container.

## Build Yourself
Run the following in the base of this directory to build a working container:
```shell
$ docker build . -t ingest
```
*Note* If this image is only living on your local machine you can uncomment the two `ENV` lines and add your `NPS_KEY` and `EVENTBRITE_TOKEN`. Otherwise, follow the instructions to pass the environment variables at runtime from your localhost.

## Pull from Docker Hub
You can also always pull the latest version of this build from Docker Hub
```shell
$ docker pull capitalnature/ingest:latest
```

## Running Container Locally
After building or pulling the container, you can pass in your environment variables and mount the `/data` folder to a local directory of your choosing to retrieve the files when it has completed its scraping.
```shell
$ docker run --env NPS_KEY --env EVENTBRITE_TOKEN -v `pwd`:/home/data ingest
```
This will run the get_events.py and push the resulting csvs to the directory of your choosing!
*Note* Do not pass the `--env` arguments if you included the environment variables on build.