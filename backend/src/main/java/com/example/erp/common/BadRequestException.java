package com.example.erp.common;

public class BadRequestException extends RuntimeException {
    public BadRequestException(String msg) { super(msg); }
}
