package com.example.erp.controller;

import com.example.erp.common.BadRequestException;
import com.example.erp.common.PageResult;
import com.example.erp.common.R;
import com.example.erp.common.NotFoundException;
import com.example.erp.entity.Inventory;
import com.example.erp.entity.Part;
import com.example.erp.repository.InventoryRepository;
import com.example.erp.repository.PartRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/inventory")
public class InventoryController {

    private final InventoryRepository repo;
    private final PartRepository partRepo;

    public InventoryController(InventoryRepository repo, PartRepository partRepo) {
        this.repo = repo;
        this.partRepo = partRepo;
    }

    @GetMapping("/warning")
    public List<Map<String, Object>> warning() {
        List<Inventory> list = repo.findWarnings();
        Map<Long, Part> partMap = partRepo.findAll().stream()
                .collect(Collectors.toMap(Part::getId, p -> p));
        return list.stream().map(inv -> {
            Map<String, Object> row = toRow(inv, partMap.get(inv.getPartId()));
            return row;
        }).collect(Collectors.toList());
    }

    @GetMapping("/page")
    public PageResult<Map<String, Object>> page(@RequestParam(defaultValue = "1") int current,
                                              @RequestParam(defaultValue = "10") int size,
                                              @RequestParam(required = false) String partName,
                                              @RequestParam(required = false) String warehouseLocation) {
        Page<Inventory> p = repo.search(partName, warehouseLocation, PageRequest.of(current - 1, size));
        Map<Long, Part> partMap = partRepo.findAll().stream()
                .collect(Collectors.toMap(Part::getId, part -> part));
        List<Map<String, Object>> rows = p.getContent().stream()
                .map(inv -> toRow(inv, partMap.get(inv.getPartId())))
                .collect(Collectors.toList());
        return new PageResult<>(rows, p.getTotalElements(), current, size);
    }

    @GetMapping("/check")
    public Map<String, Object> check() {
        List<Inventory> all = repo.findAll();
        long warnings = all.stream().filter(i -> i.getCurrentQuantity() < i.getSafetyStock()).count();
        double totalValue = all.stream().mapToDouble(i -> {
            Part p = partRepo.findById(i.getPartId()).orElse(null);
            double price = p == null || p.getPurchasePrice() == null ? 0 : p.getPurchasePrice();
            return price * (i.getCurrentQuantity() == null ? 0 : i.getCurrentQuantity());
        }).sum();
        Map<String, Object> r = new LinkedHashMap<>();
        r.put("totalSkus", all.size());
        r.put("warningCount", warnings);
        r.put("totalInventoryValue", Math.round(totalValue * 100.0) / 100.0);
        return r;
    }

    @PostMapping("/inbound")
    public R<Inventory> inbound(@RequestParam Long partId,
                               @RequestParam Integer quantity,
                               @RequestParam(required = false) String warehouseLocation) {
        if (quantity == null || quantity <= 0) throw new BadRequestException("quantity 必须 > 0");
        Inventory inv = repo.findByPartId(partId)
                .orElseGet(() -> {
                    Inventory n = new Inventory();
                    n.setPartId(partId);
                    n.setCurrentQuantity(0);
                    Part p = partRepo.findById(partId).orElse(null);
                    n.setSafetyStock(p == null || p.getStockWarningValue() == null ? 10 : p.getStockWarningValue());
                    return n;
                });
        inv.setCurrentQuantity(inv.getCurrentQuantity() + quantity);
        if (warehouseLocation != null) inv.setWarehouseLocation(warehouseLocation);
        return R.ok(repo.save(inv));
    }

    @PostMapping("/outbound")
    public R<Inventory> outbound(@RequestParam Long partId, @RequestParam Integer quantity) {
        if (quantity == null || quantity <= 0) throw new BadRequestException("quantity 必须 > 0");
        Inventory inv = repo.findByPartId(partId)
                .orElseThrow(() -> new NotFoundException("零件库存不存在: partId=" + partId));
        if (inv.getCurrentQuantity() < quantity) {
            throw new BadRequestException("库存不足：当前 " + inv.getCurrentQuantity() + "，请求 " + quantity);
        }
        inv.setCurrentQuantity(inv.getCurrentQuantity() - quantity);
        return R.ok(repo.save(inv));
    }

    @GetMapping("/get/{id}")
    public Inventory get(@PathVariable Long id) {
        return repo.findById(id)
                .orElseThrow(() -> new NotFoundException("库存记录不存在: id=" + id));
    }

    private Map<String, Object> toRow(Inventory inv, Part p) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", inv.getId());
        row.put("partId", inv.getPartId());
        row.put("currentQuantity", inv.getCurrentQuantity());
        row.put("safetyStock", inv.getSafetyStock());
        row.put("warehouseLocation", inv.getWarehouseLocation());
        if (p != null) {
            row.put("partCode", p.getPartCode());
            row.put("partName", p.getName());
            row.put("category", p.getCategory());
            row.put("unit", p.getUnit());


        }
        return row;
    }
}
