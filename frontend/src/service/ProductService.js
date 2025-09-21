//used to test database to sync with my task view page
export const ProductService = {
    getProductsMini() {
        return Promise.resolve([
            {
                id: '1000',
                name: 'Bamboo Watch',
                price: 65,
                category: 'Accessories',
                rating: 5,
                inventoryStatus: 'INSTOCK',
                image: 'bamboo-watch.jpg'
            },
            {
                id: '1001',
                name: 'Black Watch',
                price: 72,
                category: 'Accessories',
                rating: 4,
                inventoryStatus: 'LOWSTOCK',
                image: 'black-watch.jpg'
            },
            {
                id: '1002',
                name: 'Blue Band',
                price: 79,
                category: 'Fitness',
                rating: 3,
                inventoryStatus: 'INSTOCK',
                image: 'blue-band.jpg'
            },
            {
                id: '1003',
                name: 'Blue T-Shirt',
                price: 29,
                category: 'Clothing',
                rating: 5,
                inventoryStatus: 'OUTOFSTOCK',
                image: 'blue-t-shirt.jpg'
            },
            {
                id: '1004',
                name: 'Bracelet',
                price: 15,
                category: 'Accessories',
                rating: 4,
                inventoryStatus: 'INSTOCK',
                image: 'bracelet.jpg'
            }
        ]);
    }
};