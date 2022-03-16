package com.tpcstld.twozerogame;

import androidx.annotation.NonNull;

public class Cell {
    private int x;
    private int y;

    public Cell(int x, int y) {
        this.x = x;
        this.y = y;
    }

    public int getX() {
        return this.x;
    }

    void setX(int x) {
        this.x = x;
    }

    public int getY() {
        return this.y;
    }

    void setY(int y) {
        this.y = y;
    }

    @NonNull
    @Override
    public String toString() {
        return Cell.class.getSimpleName() + "{" +
                "x=" + x +
                ", y=" + y +
                '}';
    }
}
