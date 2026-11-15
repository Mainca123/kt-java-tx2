package com.ecommerce.common.events;

public record StockResultEvent(Long orderId, boolean accepted, String reason) {}
