package com.ecommerce.order;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.scheduling.annotation.EnableScheduling;
@SpringBootApplication(scanBasePackages="com.ecommerce")
@EntityScan({"com.ecommerce.order","com.ecommerce.common.outbox"})
@EnableJpaRepositories({"com.ecommerce.order","com.ecommerce.common.outbox"})
@EnableScheduling
public class OrderApplication {
  public static void main(String[] args) { SpringApplication.run(OrderApplication.class,args); }
}
