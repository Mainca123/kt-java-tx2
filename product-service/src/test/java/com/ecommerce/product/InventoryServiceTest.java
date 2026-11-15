package com.ecommerce.product;

import com.ecommerce.common.events.OrderCreatedEvent;
import com.ecommerce.common.outbox.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.*;
import java.math.BigDecimal;
import static org.assertj.core.api.Assertions.*;

@DataJpaTest(properties={"spring.jpa.hibernate.ddl-auto=create-drop","spring.jpa.show-sql=false"})
@Import({InventoryService.class,Outbox.class,InventoryServiceTest.JsonConfig.class})
class InventoryServiceTest {
    @org.springframework.boot.test.context.TestConfiguration static class JsonConfig { @Bean ObjectMapper objectMapper() { return new ObjectMapper(); } }
    @Autowired InventoryService inventory;
    @Autowired ProductRepository products;
    @Autowired ProcessedOrderRepository processed;
    @Autowired OutboxRepository outbox;
    @Test void duplicateDeliveryDeductsStockOnlyOnceAndKeepsOneResult() {
        var p=products.saveAndFlush(new Product("Test",new BigDecimal("19.95"),5));
        var event=new OrderCreatedEvent(123L,p.getId(),2);
        inventory.apply(event); inventory.apply(event);
        assertThat(products.findById(p.getId()).orElseThrow().getStock()).isEqualTo(3);
        assertThat(processed.count()).isEqualTo(1);
        assertThat(outbox.count()).isEqualTo(1);
        assertThat(outbox.findAll().get(0).getPayload()).contains("\"accepted\":true");
    }
    @Test void competingOrdersCannotMakeStockNegative() {
        var p=products.saveAndFlush(new Product("Last item",new BigDecimal("10.00"),1));
        inventory.apply(new OrderCreatedEvent(1L,p.getId(),1));
        inventory.apply(new OrderCreatedEvent(2L,p.getId(),1));
        assertThat(products.findById(p.getId()).orElseThrow().getStock()).isZero();
        assertThat(outbox.count()).isEqualTo(2);
        assertThat(outbox.findAll().stream().filter(m -> m.getPayload().contains("\"accepted\":false")).count()).isEqualTo(1);
    }
    @Test void deletedProductProducesRejectionWithoutLosingTheEvent() {
        inventory.apply(new OrderCreatedEvent(5L,999L,1));
        assertThat(processed.existsById(5L)).isTrue();
        assertThat(outbox.findAll().get(0).getPayload()).contains("\"accepted\":false");
    }
}
