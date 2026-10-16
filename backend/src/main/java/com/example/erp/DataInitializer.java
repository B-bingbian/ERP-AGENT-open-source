package com.example.erp;

import com.example.erp.entity.*;
import com.example.erp.repository.*;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 首次启动且 supplier 表为空时写入演示数据。
 * 已有数据则跳过，避免重复写入。
 */
@Component
public class DataInitializer implements CommandLineRunner {

    private final SupplierRepository supplierRepo;
    private final PartRepository partRepo;
    private final InventoryRepository inventoryRepo;
    private final PurchaseOrderRepository orderRepo;

    public DataInitializer(SupplierRepository supplierRepo,
                           PartRepository partRepo,
                           InventoryRepository inventoryRepo,
                           PurchaseOrderRepository orderRepo) {
        this.supplierRepo = supplierRepo;
        this.partRepo = partRepo;
        this.inventoryRepo = inventoryRepo;
        this.orderRepo = orderRepo;
    }

    @Override
    public void run(String... args) {
        if (supplierRepo.count() > 0) {
            return;
        }
        seed();
    }

    private void seed() {
        // ===== 5 家供应商 =====
        Supplier bosch = saveSupplier("SUP-BOSCH", "博世汽车部件（苏州）", "张工", "13800001111", "bosch@example.com",
                "江苏省苏州市工业园区", "A", 1);
        Supplier denso = saveSupplier("SUP-DENSO", "电装（广州）空调系统", "李经理", "13800002222", "denso@example.com",
                "广东省广州市黄埔区", "A", 1);
        Supplier nissin = saveSupplier("SUP-NISSIN", "日清纺制动系统（天津）", "王工", "13800003333", "nissin@example.com",
                "天津市滨海新区", "B", 1);
        Supplier zf = saveSupplier("SUP-ZF", "采埃孚传动技术（杭州）", "赵经理", "13800004444", "zf@example.com",
                "浙江省杭州市萧山区", "A", 1);
        Supplier yamaha = saveSupplier("SUP-YAMAHA", "雅马哈发动机（重庆）", "陈工", "13800005555", "yamaha@example.com",
                "重庆市九龙坡区", "B", 1);

        // ===== 10 个摩托车零部件 =====
        Part p1 = savePart("PT-SPARK-001", "铱金火花塞 CR9E", "CR9E", "M14x1.25 26.5mm", "支",
                28.0, 45.0, 50, bosch.getId(), "电气系统", "适用于多数 250-600cc 摩托车");
        Part p2 = savePart("PT-BRAKE-001", "前碟刹车片 NAO 陶瓷", "FA181", "一套两片", "套",
                85.0, 150.0, 30, nissin.getId(), "制动系统", "低粉尘、低噪声配方");
        Part p3 = savePart("PT-OIL-001", "全合成机油滤芯 HF138", "HF138", "高度 52mm", "个",
                35.0, 68.0, 60, denso.getId(), "发动机系统", "铃木/雅马哈多款通用");
        Part p4 = savePart("PT-AIR-001", "高流量空气滤芯", "ARF-2001", "海绵双层", "个",
                55.0, 98.0, 40, denso.getId(), "进气系统", "可清洗重复使用");
        Part p5 = savePart("PT-CLU-001", "离合器片套件 7 片", "CK-702", "有机摩擦片", "套",
                220.0, 380.0, 20, zf.getId(), "传动系统", "适配 400cc 级双缸");
        Part p6 = savePart("PT-CHAIN-001", "520HV 油封链条 120 节", "520HV", "节距 15.875mm", "条",
                180.0, 320.0, 25, zf.getId(), "传动系统", "抗拉强度 28kN");
        Part p7 = savePart("PT-TIRE-001", "半热熔轮胎 120/70-17", "S22", "120/70ZR17", "条",
                480.0, 780.0, 15, nissin.getId(), "行走系统", "前后通用规格，湿地性能优秀");
        Part p8 = savePart("PT-LAMP-001", "LED 前照灯总成", "HL-LED-35W", "远近光一体", "只",
                320.0, 560.0, 20, bosch.getId(), "电气系统", "6000K 白光，IP67");
        Part p9 = savePart("PT-BATT-001", "免维护蓄电池 YTZ10S", "YTZ10S", "12V 8.6Ah", "只",
                380.0, 620.0, 18, bosch.getId(), "电气系统", "适配大排量街车");
        Part p10 = savePart("PT-SHOCK-001", "后减震器（氮气）", "NTR-R1", "可调阻尼", "根",
                850.0, 1380.0, 10, yamaha.getId(), "行走系统", "24 段压缩/回弹可调");

        // ===== 库存记录：故意让部分零件低于预警值，方便 inventory_warning 演示 =====
        saveInventory(p1, 120, 50, "主仓-A1");   // 正常
        saveInventory(p2, 12,  30, "主仓-A2");   // 预警
        saveInventory(p3, 200, 60, "主仓-A1");   // 正常
        saveInventory(p4, 8,   40, "主仓-A3");   // 预警
        saveInventory(p5, 35,  20, "主仓-B1");    // 正常
        saveInventory(p6, 22,  25, "主仓-B1");    // 预警
        saveInventory(p7, 18,  15, "主仓-B2");    // 正常
        saveInventory(p8, 30,  20, "主仓-A2");   // 正常
        saveInventory(p9, 5,   18, "主仓-A2");    // 预警
        saveInventory(p10, 14, 10, "主仓-C1");   // 正常

        // ===== 2 个历史订单 =====
        PurchaseOrder o1 = new PurchaseOrder();
        o1.setOrderNumber("PO20260901001");
        o1.setTotalAmount(2800.0);
        o1.setStatus(3); // 已收货
        o1.setRemark("季度常规补货");
        o1.setSupplierId(bosch.getId());
        o1.setOrderTime(LocalDateTime.of(2026, 9, 1, 10, 30));
        OrderDetail d1 = new OrderDetail();
        d1.setPartId(p1.getId()); d1.setQuantity(50); d1.setUnitPrice(28.0); d1.setRemark("铱金火花塞");
        OrderDetail d2 = new OrderDetail();
        d2.setPartId(p8.getId()); d2.setQuantity(10); d2.setUnitPrice(320.0); d2.setRemark("LED 大灯");
        o1.getOrderDetail().add(d1);
        o1.getOrderDetail().add(d2);
        orderRepo.save(o1);

        PurchaseOrder o2 = new PurchaseOrder();
        o2.setOrderNumber("PO20260920002");
        o2.setTotalAmount(4400.0);
        o2.setStatus(1); // 已审核
        o2.setRemark("客户定制单");
        o2.setSupplierId(nissin.getId());
        o2.setOrderTime(LocalDateTime.of(2026, 9, 20, 14, 0));
        OrderDetail d3 = new OrderDetail();
        d3.setPartId(p2.getId()); d3.setQuantity(40); d3.setUnitPrice(85.0); d3.setRemark("前碟刹车片");
        OrderDetail d4 = new OrderDetail();
        d4.setPartId(p7.getId()); d4.setQuantity(5);  d4.setUnitPrice(480.0); d4.setRemark("半热熔轮胎");
        o2.getOrderDetail().add(d3);
        o2.getOrderDetail().add(d4);
        orderRepo.save(o2);

        System.out.println("=== Seed data loaded: 5 suppliers, 10 parts, 10 inventory rows, 2 orders ===");
    }

    private Supplier saveSupplier(String code, String name, String contact, String phone,
                                 String email, String addr, String rating, int status) {
        Supplier s = new Supplier();
        s.setSupplierCode(code); s.setName(name); s.setContactPerson(contact);
        s.setPhone(phone); s.setEmail(email); s.setAddress(addr);
        s.setCreditRating(rating); s.setStatus(status);
        return supplierRepo.save(s);
    }

    private Part savePart(String code, String name, String model, String spec, String unit,
                          double purchasePrice, double retail, int warning, Long supplierId,
                          String category, String desc) {
        Part p = new Part();
        p.setPartCode(code); p.setName(name); p.setModel(model); p.setSpecification(spec);
        p.setUnit(unit); p.setPurchasePrice(purchasePrice); p.setSuggestedRetailPrice(retail);
        p.setStockWarningValue(warning); p.setSupplierId(supplierId);
        p.setCategory(category); p.setDescription(desc);
        return partRepo.save(p);
    }

    private void saveInventory(Part p, int qty, int safety, String loc) {
        Inventory inv = new Inventory();
        inv.setPartId(p.getId());
        inv.setCurrentQuantity(qty);
        inv.setSafetyStock(safety);
        inv.setWarehouseLocation(loc);
        inventoryRepo.save(inv);
    }
}
