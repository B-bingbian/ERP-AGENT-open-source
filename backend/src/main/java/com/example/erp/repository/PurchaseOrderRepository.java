package com.example.erp.repository;

import com.example.erp.entity.PurchaseOrder;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface PurchaseOrderRepository extends JpaRepository<PurchaseOrder, Long> {

    @Query("SELECT o FROM PurchaseOrder o WHERE " +
           "(:orderNumber IS NULL OR o.orderNumber LIKE %:orderNumber%) AND " +
           "(:status IS NULL OR o.status = :status) AND " +
           "(:startDate IS NULL OR o.orderTime >= :startDate) AND " +
           "(:endDate IS NULL OR o.orderTime <= :endDate)")
    Page<PurchaseOrder> search(@Param("orderNumber") String orderNumber,
                               @Param("status") Integer status,
                               @Param("startDate") LocalDateTime startDate,
                               @Param("endDate") LocalDateTime endDate,
                               Pageable pageable);

    List<PurchaseOrder> findByOrderTimeBetween(LocalDateTime start, LocalDateTime end);
}
