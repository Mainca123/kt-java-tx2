package com.ecommerce.common.outbox;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.*;

@Component
public class Outbox {
    private final OutboxRepository repository;
    private final ObjectMapper mapper;
    public Outbox(OutboxRepository repository, ObjectMapper mapper) { this.repository=repository; this.mapper=mapper; }
    @Transactional(propagation=Propagation.MANDATORY)
    public void enqueue(String topic, String key, Object event) {
        try { repository.save(new OutboxMessage(topic,key,mapper.writeValueAsString(event))); }
        catch (JsonProcessingException e) { throw new IllegalStateException("Cannot encode event",e); }
    }
}
