package com.ecommerce.product;
import com.ecommerce.common.events.OrderCreatedEvent;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class OrderKafkaConsumer {
    private final InventoryService inventory;
    private final ObjectMapper mapper;
    public OrderKafkaConsumer(InventoryService inventory,ObjectMapper mapper) { this.inventory=inventory; this.mapper=mapper; }
    @KafkaListener(topics="order-events",groupId="product-group")
    public void consume(String json) throws JsonProcessingException { inventory.apply(mapper.readValue(json,OrderCreatedEvent.class)); }
}
