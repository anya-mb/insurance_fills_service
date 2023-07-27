FROM public.ecr.aws/lambda/python:3.10

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN echo ${LAMBDA_TASK_ROOT}

COPY update_lambda.py ${LAMBDA_TASK_ROOT}

CMD ["update_lambda.lambda_update"]
