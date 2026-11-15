"""Generate repetitive Maven/service configuration; source files remain editable."""
from pathlib import Path

def write(path, content):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content.strip()+'\n',encoding='utf-8')

for service in ['product-service','order-service']:
    kind=service.split('-')[0]
    write(f'{service}/pom.xml',f'''<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
<modelVersion>4.0.0</modelVersion><parent><groupId>com.ecommerce</groupId><artifactId>ecommerce-microservices</artifactId><version>1.0.0</version></parent><artifactId>{service}</artifactId>
<dependencies>
<dependency><groupId>com.ecommerce</groupId><artifactId>common</artifactId><version>${{project.version}}</version></dependency>
<dependency><groupId>com.ecommerce</groupId><artifactId>proto</artifactId><version>${{project.version}}</version></dependency>
<dependency><groupId>com.mysql</groupId><artifactId>mysql-connector-j</artifactId><scope>runtime</scope></dependency>
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-actuator</artifactId></dependency>
<dependency><groupId>net.devh</groupId><artifactId>grpc-{'server' if kind=='product' else 'client'}-spring-boot-starter</artifactId><version>3.1.0.RELEASE</version></dependency>
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-test</artifactId><scope>test</scope></dependency>
<dependency><groupId>com.h2database</groupId><artifactId>h2</artifactId><scope>test</scope></dependency>
</dependencies>
<build><plugins><plugin><groupId>org.springframework.boot</groupId><artifactId>spring-boot-maven-plugin</artifactId></plugin></plugins></build>
</project>''')
    write(f'{service}/src/main/java/com/ecommerce/{kind}/{kind.title()}Application.java',f'''
package com.ecommerce.{kind};
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.scheduling.annotation.EnableScheduling;
@SpringBootApplication(scanBasePackages="com.ecommerce")
@EntityScan({{"com.ecommerce.{kind}","com.ecommerce.common.outbox"}})
@EnableJpaRepositories({{"com.ecommerce.{kind}","com.ecommerce.common.outbox"}})
@EnableScheduling
public class {kind.title()}Application {{
  public static void main(String[] args) {{ SpringApplication.run({kind.title()}Application.class,args); }}
}}''')
    write(f'{service}/src/main/resources/application.yml',f'''
server:
  port: {8081 if kind=='product' else 8082}
  shutdown: graceful
spring:
  application:
    name: {service}
  datasource:
    url: ${{DB_URL:jdbc:mysql://localhost:3310/{kind}_db?createDatabaseIfNotExist=true&useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC}}
    username: ${{DB_USER:ecommerce}}
    password: ${{DB_PASSWORD:ecommerce_dev}}
  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: update
    properties:
      hibernate:
        jdbc:
          time_zone: UTC
  kafka:
    bootstrap-servers: ${{KAFKA_BOOTSTRAP_SERVERS:localhost:29092}}
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.apache.kafka.common.serialization.StringSerializer
      acks: all
      properties:
        enable.idempotence: true
        max.block.ms: 5000
        delivery.timeout.ms: 10000
        request.timeout.ms: 5000
    consumer:
      group-id: {kind}-group
      auto-offset-reset: earliest
      enable-auto-commit: false
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.apache.kafka.common.serialization.StringDeserializer
    listener:
      ack-mode: record
management:
  endpoints:
    web:
      exposure:
        include: health,info
  endpoint:
    health:
      probes:
        enabled: true
      show-details: always
info:
  app:
    version: ${{APP_VERSION:1.0.0}}
'''+('''grpc:
  server:
    port: 9090
app:
  seed-data: ${SEED_DATA:true}
''' if kind=='product' else '''grpc:
  client:
    product-service:
      address: ${PRODUCT_GRPC_ADDRESS:static://localhost:9090}
      negotiation-type: plaintext
'''))

write('api-gateway/pom.xml','''<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
<modelVersion>4.0.0</modelVersion><parent><groupId>com.ecommerce</groupId><artifactId>ecommerce-microservices</artifactId><version>1.0.0</version></parent><artifactId>api-gateway</artifactId>
<dependencies>
<dependency><groupId>org.springframework.cloud</groupId><artifactId>spring-cloud-starter-gateway-server-webflux</artifactId></dependency>
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-actuator</artifactId></dependency>
</dependencies>
<build><plugins><plugin><groupId>org.springframework.boot</groupId><artifactId>spring-boot-maven-plugin</artifactId></plugin></plugins></build>
</project>''')
write('api-gateway/src/main/java/com/ecommerce/gateway/GatewayApplication.java','''package com.ecommerce.gateway;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
@SpringBootApplication
public class GatewayApplication {
  public static void main(String[] args) { SpringApplication.run(GatewayApplication.class,args); }
}''')
write('api-gateway/src/main/resources/application.yml','''server:
  port: ${SERVER_PORT:8080}
  shutdown: graceful
spring:
  application:
    name: api-gateway
  cloud:
    gateway:
      server:
        webflux:
          routes:
            - id: product-service
              uri: ${PRODUCT_SERVICE_URL:http://localhost:8081}
              predicates:
                - Path=/api/products/**
            - id: order-service
              uri: ${ORDER_SERVICE_URL:http://localhost:8082}
              predicates:
                - Path=/api/orders/**
          httpclient:
            connect-timeout: 3000
            response-timeout: 10s
management:
  endpoints:
    web:
      exposure:
        include: health,info
  endpoint:
    health:
      probes:
        enabled: true
info:
  app:
    version: ${APP_VERSION:1.0.0}
''')
