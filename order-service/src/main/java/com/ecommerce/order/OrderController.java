package com.ecommerce.order;
import com.ecommerce.common.api.ApiException;
import jakarta.validation.Valid;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.data.domain.*;

@RestController @RequestMapping("/api/orders")
public class OrderController {
    private final OrderService service;
    private final OrderRepository orders;
    public OrderController(OrderService service,OrderRepository orders) { this.service=service; this.orders=orders; }
    @PostMapping @ResponseStatus(HttpStatus.CREATED)
    public CustomerOrder create(@Valid @RequestBody OrderInput input) { return service.create(input); }
    @GetMapping public java.util.List<CustomerOrder> list(@RequestParam(defaultValue="0") int page,@RequestParam(defaultValue="50") int size) {
        if (page<0 || size<1 || size>100) throw new ApiException(HttpStatus.BAD_REQUEST,"page >= 0 and 1 <= size <= 100 required");
        return orders.findAll(PageRequest.of(page,size,Sort.by(Sort.Direction.DESC,"id"))).getContent();
    }
    @GetMapping("/{id}") public CustomerOrder get(@PathVariable Long id) { return orders.findById(id).orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND,"Order not found")); }
}
