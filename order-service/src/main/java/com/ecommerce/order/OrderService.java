package com.ecommerce.order;
import com.ecommerce.common.api.ApiException;
import com.ecommerce.common.events.*;
import com.ecommerce.common.outbox.Outbox;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.math.BigDecimal;

@Service
public class OrderService {
    private final ProductClient client;
    private final OrderRepository orders;
    private final Outbox outbox;
    public OrderService(ProductClient client,OrderRepository orders,Outbox outbox) { this.client=client; this.orders=orders; this.outbox=outbox; }
    @Transactional
    public CustomerOrder create(OrderInput input) {
        var product=client.get(input.productId());
        if (product.getStock()<input.quantity()) throw new ApiException(HttpStatus.CONFLICT,"Insufficient stock");
        var order=orders.save(new CustomerOrder(product.getId(),product.getName(),input.quantity(),new BigDecimal(product.getPriceDecimal())));
        outbox.enqueue("order-events",input.productId().toString(),new OrderCreatedEvent(order.getId(),order.getProductId(),order.getQuantity()));
        return order;
    }
    @Transactional
    public void applyResult(StockResultEvent event) {
        var order=orders.findLocked(event.orderId()).orElseThrow(() -> new IllegalStateException("Order not yet visible"));
        order.complete(event.accepted(),event.reason());
    }
}
