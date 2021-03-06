# syntax=docker/dockerfile:1

FROM snakepacker/python:all as builder

RUN python3.9 -m venv /usr/share/python3/app

COPY requirements.txt .
RUN /usr/share/python3/app/bin/pip install -Ur requirements.txt

RUN find-libdeps /usr/share/python3/app > /usr/share/python3/app/pkgdeps.txt


FROM snakepacker/python:3.9

COPY --from=builder /usr/share/python3/app /usr/share/python3/app

RUN cat /usr/share/python3/app/pkgdeps.txt | xargs apt-install

RUN ln -snf /usr/share/python3/app/bin/python /usr/bin/

RUN mkdir -p /home/yandex_tv
WORKDIR /home/yandex_tv
COPY . .

ENV PATH="/usr/share/python3/app/bin:$PATH"

CMD ["python", "main.py"]