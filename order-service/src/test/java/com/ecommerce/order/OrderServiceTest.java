package com.ecommerce.order;
import com.ecommerce.common.api.ApiException;
import com.ecommerce.common.outbox.*;
import com.ecommerce.common.events.StockResultEvent;
import com.ecommerce.grpc.ProductResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.*;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

@DataJpaTest(properties={"spring.jpa.hibernate.ddl-auto=create-drop","spring.jpa.show-sql=false"})
@Import({OrderService.class,Outbox.class,OrderServiceTest.JsonConfig.class})
class OrderServiceTest {
    @org.springframework.boot.test.context.TestConfiguration static class JsonConfig { @Bean ObjectMapper objectMapper() { return new ObjectMapper(); } }
    @Autowired OrderService service;
    @Autowired OrderRepository orders;
    @Autowired OutboxRepository outbox;
    @MockitoBean ProductClient client;
    private ProductResponse product(int stock) { return ProductResponse.newBuilder().setId(1).setName("Test").setPriceDecimal("19.95").setStock(stock).build(); }
    @Test void orderAndEventAreStoredTogetherWithExactDecimalTotal() {
        when(client.get(1L)).thenReturn(product(10));
        var order=service.create(new OrderInput(1L,3));
        assertThat(order.getTotalPrice()).isEqualByComparingTo("59.85");
        assertThat(order.getStatus()).isEqualTo("PENDING");
        assertThat(outbox.count()).isEqualTo(1);
        assertThat(outbox.findAll().get(0).getPayload()).contains("\"orderId\":"+order.getId());
    }
    @Test void insufficientStockCreatesNeitherOrderNorEvent() {
        when(client.get(1L)).thenReturn(product(0));
        assertThatThrownBy(() -> service.create(new OrderInput(1L,1))).isInstanceOf(ApiException.class);
        assertThat(orders.count()).isZero(); assertThat(outbox.count()).isZero();
    }
    @Test void repeatedResultDoesNotChangeACompletedOrder() {
        when(client.get(1L)).thenReturn(product(10));
        var order=service.create(new OrderInput(1L,1));
        service.applyResult(new StockResultEvent(order.getId(),true,"ok"));
        service.applyResult(new StockResultEvent(order.getId(),false,"duplicate"));
        assertThat(orders.findById(order.getId()).orElseThrow().getStatus()).isEqualTo("CONFIRMED");
    }
}
