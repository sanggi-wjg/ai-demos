create table `category`
(
    `id`   integer      not null auto_increment comment 'PK',
    `name` varchar(255) not null comment '카테고리 이름',
    primary key (`id`)
) engine=InnoDB

create table `product`
(
    `id`   integer      not null auto_increment comment 'PK',
    `name` varchar(255) not null comment '상품 이름',
    primary key (`id`)
) engine=InnoDB

create table `product_category_mapping`
(
    `id`          integer not null auto_increment comment 'PK',
    `category_id` integer not null comment '카테고리 PK로 외래키',
    `product_id`  integer not null comment '상품 PK로 외래키',
    primary key (`id`)
) engine=InnoDB

create table `product_option`
(
    `id`         integer        not null auto_increment comment 'PK',ㅈ
    `price`      decimal(38, 2) not null comment '상품 옵션 가격',
    `product_id` integer        not null comment '상품 PK로 외래키',
    `name`       varchar(255)   comment '상품 옵션 이름',
    primary key (`id`)
) engine=InnoDB

alter table `product_category_mapping`
    add constraint `FKo6nrpr0lgmih64v62rqcg1ree` foreign key (`category_id`) references `category` (`id`)

alter table `product_category_mapping`
    add constraint `FKbcw8a90rd65jy0vaeu5facs28` foreign key (`product_id`) references `product` (`id`)

alter table `product_option`
    add constraint `FK1p9oriljjorsv35p5s05meh47` foreign key (`product_id`) references `product` (`id`)
