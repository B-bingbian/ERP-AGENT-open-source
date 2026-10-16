package com.example.erp.controller;

import com.example.erp.common.BadRequestException;
import com.example.erp.common.PageResult;
import com.example.erp.common.R;
import com.example.erp.common.NotFoundException;
import com.example.erp.entity.OrderDetail;
import com.example.erp.entity.Part;
import com.example.erp.entity.PurchaseOrder;
import com.example.erp.entity.Supplier;
import com.example.erp.repository.OrderDetailRepository;
import com.example.erp.repository.PartRepository;
import com.example.erp.repository.PurchaseOrderRepository;
import com.example.erp.repository.SupplierRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    private final PurchaseOrderRepository orderRepo;
    private final OrderDetailRepository detailRepo;
    private final PartRepository partRepo;
    private final SupplierRepository supplierRepo;

    public OrderController(PurchaseOrderRepository orderRepo,
                          OrderDetailRepository detailRepo,
                          PartRepository partRepo,
                          SupplierRepository supplierRepo) {
        this.orderRepo = orderRepo;
        this.detailRepo = detailRepo;
        this.partRepo = partRepo;
        this.supplierRepo = supplierRepo;
    }

    @PostMapping("/create")
    public R<PurchaseOrder> create(@RequestBody PurchaseOrder body) {
        if (body.getOrderNumber() == null || body.getOrderNumber().isBlank()) {
            throw new BadRequestException("orderNumber 为必填");
        }
        if (body.getOrderDetail() == null || body.getOrderDetail().isEmpty()) {
            throw new BadRequestException("orderDetail 至少一条明细");
        }
        body.getOrderDetail().forEach(d -> {
            if (d.getQuantity() == null || d.getQuantity() < 1) throw new BadRequestException("quantity >= 1");
            if (d.getUnitPrice() == null || d.getUnitPrice() <= 0) throw new BadRequestException("unitPrice > 0");
            if (d.getPartId() == null) throw new BadRequestException("partId 为必填");
        });
        if (body.getTotalAmount() == null) {
            double sum = body.getOrderDetail().stream()
                    .mapToDouble(d -> d.getQuantity() * d.getUnitPrice()).sum();
            body.setTotalAmount(Math.round(sum * 100.0) / 100.0);
        }
        if (body.getStatus() == null) body.setStatus(0);
        return R.ok(orderRepo.save(body));
    }

    @PutMapping("/update/{id}")
    public R<PurchaseOrder> update(@PathVariable Long id, @RequestBody PurchaseOrder body) {
        PurchaseOrder o = orderRepo.findById(id)
                .orElseThrow(() -> new NotFoundException("订单不存在: id=" + id));
        if (body.getOrderNumber() != null) o.setOrderNumber(body.getOrderNumber());
        if (body.getTotalAmount() != null) o.setTotalAmount(body.getTotalAmount());
        if (body.getRemark() != null) o.setRemark(body.getRemark());
        if (body.getStatus() != null) o.setStatus(body.getStatus());
        if (body.getOrderDetail() != null && !body.getOrderDetail().isEmpty()) {
            o.getOrderDetail().clear();
            o.getOrderDetail().addAll(body.getOrderDetail());
        }
        return R.ok(orderRepo.save(o));
    }

    @GetMapping("/page")
    public PageResult<PurchaseOrder> page(@RequestParam(defaultValue = "1") int current,
                                         @RequestParam(defaultValue = "10") int size,
                                         @RequestParam(required = false) String orderNumber,
                                         @RequestParam(required = false) Integer status,
                                         @RequestParam(required = false) String startDate,
                                         @RequestParam(required = false) String endDate) {
        LocalDateTime start = startDate == null ? null : LocalDate.parse(startDate).atStartOfDay();
        LocalDateTime end = endDate == null ? null : LocalDate.parse(endDate).atTime(LocalTime.MAX);
        Page<PurchaseOrder> p = orderRepo.search(orderNumber, status, start, end, PageRequest.of(current - 1, size));
        return new PageResult<>(p.getContent(), p.getTotalElements(), current, size);
    }

    @GetMapping("/get/{id}")
    public PurchaseOrder get(@PathVariable Long id) {
        return orderRepo.findById(id)
                .orElseThrow(() -> new NotFoundException("订单不存在: id=" + id));
    }

    @GetMapping("/search-details")
    public List<Map<String, Object>> searchDetails(@RequestParam(required = false) String partName,
                                                    @RequestParam(required = false) String startDate,
                                                    @RequestParam(required = false) String endDate) {
        LocalDateTime start = parseDate(startDate, true);
        LocalDateTime end = parseDate(endDate, false);
        List<OrderDetail> details = detailRepo.searchDetails(partName, start, end);
        Map<Long, Part> partMap = partRepo.findAll().stream()
                .collect(Collectors.toMap(Part::getId, p -> p));
        Map<Long, Supplier> supMap = supplierRepo.findAll().stream()
                .collect(Collectors.toMap(Supplier::getId, s -> s));

        return details.stream().map(d -> {
            Map<String, Object> row = new HashMap<>();
            row.put("detailId", d.getId());
            row.put("orderId", d.getOrderId());
            row.put("partId", d.getPartId());
            row.put("quantity", d.getQuantity());
            row.put("unitPrice", d.getUnitPrice());
            Part p = partMap.get(d.getPartId());
            row.put("partName", p == null ? null : p.getName());
            row.put("partCode", p == null ? null : p.getPartCode());
            if (p != null && p.getSupplierId() != null) {
                Supplier s = supMap.get(p.getSupplierId());
                row.put("supplierName", s == null ? null : s.getName());
            }
            return row;
        }).collect(Collectors.toList());
    }

    @GetMapping("/statistics")
    public Map<String, Object> statistics(@RequestParam(required = false) String startDate,
                                         @RequestParam(required = false) String endDate) {
        LocalDateTime start = parseDate(startDate, true);
        LocalDateTime end = parseDate(endDate, false);
        List<PurchaseOrder> orders;
        if (start != null || end != null) {
            LocalDateTime s = start == null ? LocalDateTime.of(2000,1,1,0,0) : start;
            LocalDateTime e = end == null ? LocalDateTime.of(2999,12,31,23,59,59) : end;
            orders = orderRepo.findByOrderTimeBetween(s, e);
        } else {
            orders = orderRepo.findAll();
        }
        Map<Integer, Long> byStatus = orders.stream()
                .collect(Collectors.groupingBy(o -> o.getStatus() == null ? 0 : o.getStatus(), Collectors.counting()));
        double total = orders.stream().mapToDouble(o -> o.getTotalAmount() == null ? 0 : o.getTotalAmount()).sum();

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("totalOrders", orders.size());
        result.put("totalAmount", Math.round(total * 100.0) / 100.0);
        result.put("byStatus", byStatus);
        return result;
    }

    @PatchMapping("/update-status/{id}")
    public R<PurchaseOrder> updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        PurchaseOrder o = orderRepo.findById(id)
                .orElseThrow(() -> new NotFoundException("订单不存在: id=" + id));
        o.setStatus(status);
        return R.ok(orderRepo.save(o));
    }

    private LocalDateTime parseDate(String s, boolean startOfDay) {
        if (s == null || s.isBlank()) return null;
        try {
            if (s.length() == 10) return LocalDate.parse(s).atStartOfDay();
            return LocalDateTime.parse(s.replace(' ', 'T'));
        } catch (Exception e) {
            return null;
        }
    }
}
