package com.ecommerce.order;
import jakarta.validation.constraints.*;
public record OrderInput(@NotNull @Positive Long productId,@NotNull @Min(1) @Max(10000) Integer quantity) {}
