package com.example.erp.repository;

import com.example.erp.entity.OrderDetail;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface OrderDetailRepository extends JpaRepository<OrderDetail, Long> {

    List<OrderDetail> findByOrderIdIn(List<Long> orderIds);

    @Query("SELECT d FROM OrderDetail d JOIN PurchaseOrder o ON d.orderId = o.id WHERE " +
           "(:partName IS NULL OR d.partId IN (SELECT p.id FROM Part p WHERE p.name LIKE %:partName%)) AND " +
           "(:startDate IS NULL OR o.orderTime >= :startDate) AND " +
           "(:endDate IS NULL OR o.orderTime <= :endDate)")
    List<OrderDetail> searchDetails(@Param("partName") String partName,
                                    @Param("startDate") LocalDateTime startDate,
                                    @Param("endDate") LocalDateTime endDate);
}
