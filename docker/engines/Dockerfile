FROM maven:3.9.12-eclipse-temurin-25 AS build

WORKDIR /build
COPY engine-service/pom.xml ./
RUN mvn -B -q dependency:go-offline
COPY engine-service/src ./src
RUN mvn -B -q package -DskipTests

FROM eclipse-temurin:25-jre

ENV CONTINUUM_ENGINE=jena \
    CONTINUUM_PORT=8080

WORKDIR /app
COPY --from=build /build/target/semantic-engine-service-0.1.0.jar /app/engine.jar

EXPOSE 8080

CMD ["java", "-Xms256m", "-Xmx2g", "-jar", "/app/engine.jar"]
