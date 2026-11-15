package com.ecommerce.product;
import com.ecommerce.grpc.*;
import io.grpc.Status;
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;

@GrpcService
public class ProductGrpcService extends ProductServiceGrpc.ProductServiceImplBase {
    private final ProductRepository repository;
    public ProductGrpcService(ProductRepository repository) { this.repository=repository; }
    @Override public void getProductById(ProductRequest request, StreamObserver<ProductResponse> observer) {
        if (request.getId()<1) { observer.onError(Status.INVALID_ARGUMENT.withDescription("productId must be positive").asRuntimeException()); return; }
        var found=repository.findById(request.getId());
        if (found.isEmpty()) { observer.onError(Status.NOT_FOUND.withDescription("Product not found").asRuntimeException()); return; }
        var p=found.get();
        observer.onNext(ProductResponse.newBuilder().setId(p.getId()).setName(p.getName()).setPrice(p.getPrice().doubleValue())
                .setPriceDecimal(p.getPrice().toPlainString()).setStock(p.getStock()).build()); observer.onCompleted();
    }
}
