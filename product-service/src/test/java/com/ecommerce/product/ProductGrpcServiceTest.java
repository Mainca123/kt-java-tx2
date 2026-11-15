package com.ecommerce.product;
import com.ecommerce.grpc.*;
import io.grpc.*;
import io.grpc.stub.StreamObserver;
import org.junit.jupiter.api.Test;
import java.util.Optional;
import java.math.BigDecimal;
import static org.mockito.Mockito.*;
import static org.assertj.core.api.Assertions.*;

class ProductGrpcServiceTest {
    @Test void missingProductReturnsNotFoundInsteadOfUnknown() {
        var repo=mock(ProductRepository.class);
        when(repo.findById(99L)).thenReturn(Optional.empty());
        @SuppressWarnings("unchecked") StreamObserver<ProductResponse> observer=mock(StreamObserver.class);
        new ProductGrpcService(repo).getProductById(ProductRequest.newBuilder().setId(99).build(),observer);
        verify(observer).onError(argThat(e -> Status.fromThrowable(e).getCode()==Status.Code.NOT_FOUND));
        verify(observer,never()).onNext(any());
    }
}
