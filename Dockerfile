FROM python:3.8

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y tesseract-ocr \
    libopencv-dev
#    python3-opencv

WORKDIR /app
COPY ./app /app
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN python -m pip install opencv-python\
    && pip install img2table \
    && pip install requests \
    && pip install pdf2image
RUN apt-get install -y poppler-utils

EXPOSE 3000
CMD ["python", "main.py"]

