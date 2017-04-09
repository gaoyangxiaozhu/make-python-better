read a tree architecrture from md:
such as the content in **xx.md** is 
```shell
    + category1
        - file1
        - file2
        + category1_1
            - file1_1
            - file1_2
            + category1_1_1
                - file1_1_1
            - file1_3
        + category1_2
            - file1_2_1
    + category2
        - file3
        - file4
        + category2_1
            - file2_1_1
        - file5
    + category3
        - file6
    - file7

```

then by runing `python generate_tree_nav.py`
we can get a global_category dict which storage the total directory architecrure
and can be using to rebuild the total directory architecture recursively



