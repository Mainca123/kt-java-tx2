package com.ecommerce.common.events;

public record OrderCreatedEvent(Long orderId, Long productId, int quantity) {}
