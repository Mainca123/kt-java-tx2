package com.ecommerce.common.outbox;

import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.domain.Pageable;
import java.util.List;

public interface OutboxRepository extends JpaRepository<OutboxMessage,Long> {
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select m from OutboxMessage m order by m.id")
    List<OutboxMessage> lockBatch(Pageable page);
}
