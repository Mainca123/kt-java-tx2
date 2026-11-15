package com.ecommerce.product;
import com.ecommerce.common.events.*;
import com.ecommerce.common.outbox.Outbox;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.slf4j.*;

@Service
public class InventoryService {
    private static final Logger log=LoggerFactory.getLogger(InventoryService.class);
    private final ProductRepository products;
    private final ProcessedOrderRepository processed;
    private final Outbox outbox;
    public InventoryService(ProductRepository products,ProcessedOrderRepository processed,Outbox outbox) { this.products=products; this.processed=processed; this.outbox=outbox; }
    @Transactional
    public void apply(OrderCreatedEvent event) {
        // Lock product first. Duplicate events for this product are serialized even across replicas.
        var product=products.findLocked(event.productId());
        if (processed.existsById(event.orderId())) return;
        boolean accepted=product.isPresent() && event.quantity()>0 && product.get().getStock()>=event.quantity();
        String reason=accepted ? "Stock deducted" : "Product missing or insufficient stock at fulfillment";
        if (accepted) product.get().deduct(event.quantity());
        processed.save(new ProcessedOrder(event.orderId(),accepted,reason));
        outbox.enqueue("stock-results",event.orderId().toString(),new StockResultEvent(event.orderId(),accepted,reason));
        log.info("Order {}: accepted={}, product={}, quantity={}",event.orderId(),accepted,event.productId(),event.quantity());
    }
}
