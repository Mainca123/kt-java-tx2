package com.ecommerce.common.outbox;

import org.springframework.data.domain.PageRequest;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionTemplate;
import org.slf4j.*;
import java.util.concurrent.TimeUnit;

@Component
public class OutboxPublisher {
    private static final Logger log=LoggerFactory.getLogger(OutboxPublisher.class);
    private final OutboxRepository repository;
    private final KafkaTemplate<String,String> kafka;
    private final TransactionTemplate transactions;
    public OutboxPublisher(OutboxRepository repository, KafkaTemplate<String,String> kafka, TransactionTemplate transactions) {
        this.repository=repository; this.kafka=kafka; this.transactions=transactions;
    }
    @Scheduled(fixedDelayString="${app.outbox-delay-ms:500}")
    public void publish() {
        try {
            transactions.executeWithoutResult(tx -> {
                for (var message: repository.lockBatch(PageRequest.of(0,20))) {
                    try { kafka.send(message.getTopic(),message.getMessageKey(),message.getPayload()).get(10,TimeUnit.SECONDS); }
                    catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new IllegalStateException(e); }
                    catch (Exception e) { throw new IllegalStateException("Kafka unavailable; outbox retained for retry",e); }
                    repository.delete(message);
                }
            });
        } catch (Exception e) { log.warn("Outbox retry: {}",e.getMessage()); }
    }
}
