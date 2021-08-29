# NOTE


## TODO

- 行末のバックスラッシュを処理する
- 複数行コメントを処理する
- (unused) メンバを誤ってエラー扱いしないようにする


## Validate directives

### unused

`unused x`
- 以降の行で変数xを使用しないことを表明する
  - 影響範囲は現在のスコープ内のみ

```cpp
    int i;
    {
        for (i = 0; i < 10; i++) {}
        //!unused i
        printf("%d\n", i);  //=> Error: Variable 'i' can not be used.
    }
    printf("%d\n", i);  //=> ok
```

