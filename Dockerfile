FROM python:2.7
ADD ./rscraper /code/rscraper
ADD scrapeAll.py /code/scrapeAll.py
ADD config/requirements.txt /code/requirements.txt
WORKDIR /code
RUN pip install -r /code/requirements.txt
CMD python scrapeAll.py
