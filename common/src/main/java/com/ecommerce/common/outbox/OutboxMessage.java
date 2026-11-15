package com.ecommerce.common.outbox;

import jakarta.persistence.*;
import java.time.Instant;

@Entity @Table(name="outbox_messages")
public class OutboxMessage {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
    @Column(nullable=false) private String topic;
    @Column(name="message_key", nullable=false) private String messageKey;
    @Column(nullable=false, columnDefinition="TEXT") private String payload;
    @Column(nullable=false) private Instant createdAt = Instant.now();
    protected OutboxMessage() {}
    public OutboxMessage(String topic, String key, String payload) { this.topic=topic; this.messageKey=key; this.payload=payload; }
    public String getTopic() { return topic; }
    public String getMessageKey() { return messageKey; }
    public String getPayload() { return payload; }
}
