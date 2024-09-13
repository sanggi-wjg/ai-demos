create table `category`
(
    `id`   integer      not null auto_increment comment '카테고리 PK',
    `name` varchar(255) not null comment '카테고리 이름',
    primary key (`id`)
) engine=InnoDB

create table `product`
(
    `id`   integer      not null auto_increment comment '상품 PK',
    `name` varchar(255) not null comment '상품 이름',
    primary key (`id`)
) engine=InnoDB

create table `product_category_mapping`
(
    `id`          integer not null auto_increment comment '상품 카테고리 매핑 PK',
    `category_id` integer not null comment '카테고리 PK로 외래키',
    `product_id`  integer not null comment '상품 PK로 외래키',
    primary key (`id`)
) engine=InnoDB

create table `product_option`
(
    `id`         integer        not null auto_increment comment '상품 옵션 PK',
    `price`      decimal(38, 2) not null comment '상품 옵션 가격',
    `product_id` integer        not null comment '상품 PK로 외래키',
    `name`       varchar(255) comment '상품 옵션 이름',
    primary key (`id`)
) engine=InnoDB

alter table `product_category_mapping`
    add constraint `FKo6nrpr0lgmih64v62rqcg1ree` foreign key (`category_id`) references `category` (`id`)

alter table `product_category_mapping`
    add constraint `FKbcw8a90rd65jy0vaeu5facs28` foreign key (`product_id`) references `product` (`id`)

alter table `product_option`
    add constraint `FK1p9oriljjorsv35p5s05meh47` foreign key (`product_id`) references `product` (`id`)


create table `sku`
(
    `id`             integer        not null auto_increment comment 'SKU PK',
    `name`           varchar(255)   not null comment 'SKU 이름',
    `code`           varchar(255)   not null comment 'SKU 코드',
    `original_price` decimal(38, 2) not null comment 'SKU 원가',
    `stock_quantity` integer        not null comment 'SKU 재고수',
    primary key (`id`)
) engine=InnoDB

create table `sku_product_option_mapping`
(
    `id`                integer not null auto_increment comment 'SKU 옵션 PK',
    `sku_id`            integer not null comment 'SKU PK로 외래키',
    `product_option_id` integer not null comment '상품 옵션 PK로 외래키',
    `sales_count`       integer not null comment '상품 옵션의 SKU 판매 개수, 값이 3이라면 해당 상품 옵션으로 1개 판매시 SKU는 3개 판매',
    primary key (`id`)
) engine=InnoDB

alter table `sku_product_option_mapping`
    add constraint `FK_spom_sku_id` foreign key (`sku_id`) references `sku` (`id`)

alter table `sku_product_option_mapping`
    add constraint `FK_spom_product_option_id` foreign key (`product_option_id`) references `product_option` (`id`)


create table `order`
(
    `id`         integer        not null auto_increment comment '주문 PK',
    `user_id`    integer        not null comment '사용자 PK로 외래키',
    `amount`     decimal(38, 2) not null comment '주문 상품 가격 합계',
    `created_at` datetime(6)    not null comment '주문 생성시간',
    primary key (`id`)
) engine=InnoDB

create table `order_item`
(
    `id`                integer        not null auto_increment comment '주문 상품 PK',
    `product_id`        integer        not null comment '상품 PK로 외래키',
    `product_option_id` integer        not null comment '상품 옵션 PK로 외래키',
    `order_id`          integer        not null comment '주문 PK로 외래키',
    `price`             decimal(38, 2) not null comment '주문 시점, 상품 옵션 가격',
    `quantity`          integer        not null comment '주문 시점, 상품 옵션 구매수',
    primary key (`id`)
) engine=InnoDB

alter table `order`
    add constraint `FK_order_user_id` foreign key (`user_id`) references `user` (`id`)

alter table `order_item`
    add constraint `FK_order_item_product_id` foreign key (`product_id`) references `product` (`id`)

alter table `order_item`
    add constraint `FK_order_item_option_id` foreign key (`product_option_id`) references `product_option` (`id`)

alter table `order_item`
    add constraint `FK_order_item_order_id` foreign key (`order_id`) references `order` (`id`)
