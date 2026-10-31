# syntax=docker/dockerfile:1.7
# Tek Dockerfile, dört servis: docker compose her servis için MODUL argümanını verir.
# Derleme konteynerde yapılır; bilgisayarda Java/Maven gerekmez.

FROM maven:3.9-eclipse-temurin-21 AS derleme
ARG MODUL
WORKDIR /src
COPY pom.xml .
COPY common common
COPY data-loader data-loader
COPY election-api election-api
COPY gateway gateway
COPY chatbot chatbot
RUN --mount=type=cache,target=/root/.m2 mvn -B -q -pl ${MODUL} -am package -DskipTests

FROM eclipse-temurin:21-jre
ARG MODUL
WORKDIR /app
COPY --from=derleme /src/${MODUL}/target/${MODUL}.jar app.jar
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/app/app.jar"]
