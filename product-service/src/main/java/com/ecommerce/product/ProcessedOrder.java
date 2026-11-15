package com.ecommerce.product;
import jakarta.persistence.*;

@Entity @Table(name="processed_orders")
public class ProcessedOrder {
    @Id private Long orderId;
    private boolean accepted;
    private String reason;
    protected ProcessedOrder() {}
    public ProcessedOrder(Long orderId,boolean accepted,String reason) { this.orderId=orderId; this.accepted=accepted; this.reason=reason; }
}
