package com.ecommerce.common.events;

import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.context.annotation.*;
import org.springframework.kafka.config.TopicBuilder;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.util.backoff.FixedBackOff;

@Configuration
public class KafkaTopics {
    @Bean NewTopic ordersTopic() { return TopicBuilder.name("order-events").partitions(3).replicas(1).build(); }
    @Bean NewTopic resultsTopic() { return TopicBuilder.name("stock-results").partitions(3).replicas(1).build(); }
    // Keep retrying transient DB/consumer failures rather than silently discarding orders.
    @Bean DefaultErrorHandler kafkaErrorHandler() {
        return new DefaultErrorHandler(new FixedBackOff(1000L,FixedBackOff.UNLIMITED_ATTEMPTS));
    }
}
