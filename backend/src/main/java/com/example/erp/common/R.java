package com.example.erp.common;

/**
 * 写操作统一返回。查询接口直接返回业务对象，不包 R。
 */
public class R<T> {
    private int code;
    private String message;
    private T data;

    public R() {}
    public R(int code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }
    public static <T> R<T> ok(T data) { return new R<>(200, "success", data); }
    public static <T> R<T> fail(int code, String msg) { return new R<>(code, msg, null); }

    public int getCode() { return code; }
    public String getMessage() { return message; }
    public T getData() { return data; }
}
