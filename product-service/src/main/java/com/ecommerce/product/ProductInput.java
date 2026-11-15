package com.ecommerce.product;
import jakarta.validation.constraints.*;
import java.math.BigDecimal;

public record ProductInput(@NotBlank @Size(max=150) String name,
        @NotNull @DecimalMin("0.01") @Digits(integer=10,fraction=2) BigDecimal price,
        @NotNull @Min(0) Integer stock) {}
