## Insurance Fills Service

This service allows a user (the one who wants to make a claim) to describe the claim / problem, answer additional questions and the result claim will be stored in the Insurance company database.

The project is done as infrastructure-as-a-code using AWS CDK which creates CloudFormation template. AWS Lambda is deployed as a Docker image because it allows to store 10Gb in dependencies, otherwise the limit is up to 128 Mb for all dependencies.

Lambda goes to OpenAI language models for parcing the user answer and ask additional questions. Then the claimed is stored in AWS S3 bucket.

Add OpenAI api key `OPENAI_API_KEY` to `.env` file to run `notebooks/` files.


## Setup

To install dependencies:

```
poetry install
```

Install pre-commit hooks:
```
poetry run pre-commit install
```


Add new python dependency:
```
poetry add new-package-name
```


### Deployment


Activate environment (optional):
```
poetry shell
```

Export environment variables for AWS CDK:

```
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
```

To deploy on Mac OS:

```
DOCKER_DEFAULT_PLATFORM=linux/amd64 cdk deploy  --all
```
