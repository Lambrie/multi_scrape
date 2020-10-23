FROM python:3.7-slim-buster

RUN apt-get update
#RUN apt-get install -y libffi-dev libssl-dev

WORKDIR /google_business_cards

ENV PYTHONUNBUFFERED 1

#EXPOSE 443
#EXPOSE 80

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY google_places_scrape.py /google_business_cards

CMD ["python", "google_places_scrape.py"]