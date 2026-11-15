package com.ecommerce.order;
import com.ecommerce.grpc.*;
import com.ecommerce.common.api.ApiException;
import io.grpc.*;
import net.devh.boot.grpc.client.inject.GrpcClient;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import java.util.concurrent.TimeUnit;

@Component
public class ProductClient {
    @GrpcClient("product-service") private ProductServiceGrpc.ProductServiceBlockingStub stub;
    public ProductResponse get(Long id) {
        try { return stub.withWaitForReady().withDeadlineAfter(3,TimeUnit.SECONDS).getProductById(ProductRequest.newBuilder().setId(id).build()); }
        catch (StatusRuntimeException e) {
            throw switch(e.getStatus().getCode()) {
                case NOT_FOUND -> new ApiException(HttpStatus.NOT_FOUND,"Product not found");
                case INVALID_ARGUMENT -> new ApiException(HttpStatus.BAD_REQUEST,"Invalid productId");
                default -> new ApiException(HttpStatus.SERVICE_UNAVAILABLE,"Product service unavailable; retry later");
            };
        }
    }
}
