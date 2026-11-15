package com.ecommerce.product;
import com.ecommerce.common.api.ApiException;
import jakarta.validation.Valid;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.data.domain.*;

@RestController @RequestMapping("/api/products")
public class ProductController {
    private final ProductRepository repository;
    public ProductController(ProductRepository repository) { this.repository=repository; }
    @GetMapping public java.util.List<Product> list(@RequestParam(defaultValue="0") int page, @RequestParam(defaultValue="50") int size) {
        if (page<0 || size<1 || size>100) throw new ApiException(HttpStatus.BAD_REQUEST,"page >= 0 and 1 <= size <= 100 required");
        return repository.findAll(PageRequest.of(page,size,Sort.by("id"))).getContent();
    }
    @GetMapping("/{id}") public Product get(@PathVariable Long id) { return repository.findById(id).orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND,"Product not found")); }
    @PostMapping @ResponseStatus(HttpStatus.CREATED)
    public Product create(@Valid @RequestBody ProductInput input) { return repository.save(new Product(input.name().trim(),input.price(),input.stock())); }
    @PutMapping("/{id}") @Transactional
    public Product update(@PathVariable Long id,@Valid @RequestBody ProductInput input) {
        Product p=repository.findLocked(id).orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND,"Product not found"));
        p.update(input.name().trim(),input.price(),input.stock()); return p;
    }
    @DeleteMapping("/{id}") @ResponseStatus(HttpStatus.NO_CONTENT) @Transactional
    public void delete(@PathVariable Long id) {
        Product p=repository.findLocked(id).orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND,"Product not found")); repository.delete(p);
    }
}
