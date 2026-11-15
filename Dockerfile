FROM eclipse-temurin:17-jre-alpine
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
ARG SERVICE
COPY ${SERVICE}/target/${SERVICE}-1.0.0.jar app.jar
USER app
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=65.0 -XX:InitialRAMPercentage=20.0" SERVER_PORT=8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=90s --retries=10 CMD wget -q -O - http://localhost:${SERVER_PORT}/actuator/health/readiness || exit 1
ENTRYPOINT ["java","-jar","/app/app.jar"]
