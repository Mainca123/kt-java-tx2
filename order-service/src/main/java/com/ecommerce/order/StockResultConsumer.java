package com.ecommerce.order;
import com.ecommerce.common.events.StockResultEvent;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class StockResultConsumer {
    private final OrderService orders;
    private final ObjectMapper mapper;
    public StockResultConsumer(OrderService orders,ObjectMapper mapper) { this.orders=orders; this.mapper=mapper; }
    @KafkaListener(topics="stock-results",groupId="order-group")
    public void consume(String json) throws JsonProcessingException { orders.applyResult(mapper.readValue(json,StockResultEvent.class)); }
}
