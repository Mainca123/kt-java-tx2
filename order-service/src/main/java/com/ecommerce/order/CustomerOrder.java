package com.ecommerce.order;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity @Table(name="orders")
public class CustomerOrder {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
    @Column(nullable=false) private Long productId;
    @Column(nullable=false) private String productName;
    @Column(nullable=false) private int quantity;
    @Column(nullable=false,precision=12,scale=2) private BigDecimal unitPrice;
    @Column(nullable=false,precision=22,scale=2) private BigDecimal totalPrice;
    @Column(nullable=false) private String status="PENDING";
    private String reason;
    @Column(nullable=false) private Instant createdAt=Instant.now();
    protected CustomerOrder() {}
    public CustomerOrder(Long productId,String name,int quantity,BigDecimal unitPrice) {
        this.productId=productId; this.productName=name; this.quantity=quantity; this.unitPrice=unitPrice; this.totalPrice=unitPrice.multiply(BigDecimal.valueOf(quantity));
    }
    public Long getId() { return id; }
    public Long getProductId() { return productId; }
    public String getProductName() { return productName; }
    public int getQuantity() { return quantity; }
    public BigDecimal getUnitPrice() { return unitPrice; }
    public BigDecimal getTotalPrice() { return totalPrice; }
    public String getStatus() { return status; }
    public String getReason() { return reason; }
    public Instant getCreatedAt() { return createdAt; }
    public void complete(boolean accepted,String reason) { if ("PENDING".equals(status)) { this.status=accepted?"CONFIRMED":"REJECTED"; this.reason=reason; } }
}
