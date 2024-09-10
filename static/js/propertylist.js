// document.addEventListener("DOMContentLoaded", function () {
//     // Carousel Functionality
//     const carousels = document.querySelectorAll('.carousel');
//     carousels.forEach(carousel => {
//         let items = carousel.querySelectorAll('.carousel-item');
//         let currentIndex = 0;

//         function showSlide(index) {
//             items.forEach((item, i) => {
//                 item.classList.toggle('active', i === index);
//             });
//         }

//         showSlide(currentIndex);
//         setInterval(() => {
//             currentIndex = (currentIndex + 1) % items.length;
//             showSlide(currentIndex);
//         }, 3000); // Change slide every 3 seconds
//     });

//     // Toggle Buttons Functionality
//     const toggleRent = document.getElementById('toggle-rent');
//     const toggleSale = document.getElementById('toggle-sale');
//     const propertyCards = document.querySelectorAll('.property-card');

//     function filterProperties(type) {
//         propertyCards.forEach(card => {
//             if (card.dataset.type === type || type === 'all') {
//                 card.style.display = 'block';
//             } else {
//                 card.style.display = 'none';
//             }
//         });
//     }

//     toggleRent.addEventListener('click', function () {
//         filterProperties('rent');
//         toggleRent.classList.add('active');
//         toggleSale.classList.remove('active');
//     });

//     toggleSale.addEventListener('click', function () {
//         filterProperties('sale');
//         toggleSale.classList.add('active');
//         toggleRent.classList.remove('active');
//     });

//     // Initial Load - Show Rent Properties
//     filterProperties('rent');
// });





// document.addEventListener("DOMContentLoaded", function () {
//     // Carousel Functionality
//     const carousels = document.querySelectorAll('.carousel');
//     carousels.forEach(carousel => {
//         let items = carousel.querySelectorAll('.carousel-item');
//         let currentIndex = 0;

//         function showSlide(index) {
//             items.forEach((item, i) => {
//                 item.classList.toggle('active', i === index);
//             });
//         }

//         if (items.length > 0) {
//             showSlide(currentIndex);
//             setInterval(() => {
//                 currentIndex = (currentIndex + 1) % items.length;
//                 showSlide(currentIndex);
//             }, 3000); // Change slide every 3 seconds
//         }
//     });

//     // Toggle Buttons Functionality
//     const toggleRent = document.getElementById('toggle-rent');
//     const toggleSale = document.getElementById('toggle-sale');
//     const propertyCards = document.querySelectorAll('.property-card');

//     function filterProperties(type) {
//         let found = false;
//         propertyCards.forEach(card => {
//             if (card.dataset.type === type || type === 'all') {
//                 card.style.display = 'block';
//                 found = true;
//             } else {
//                 card.style.display = 'none';
//             }
//         });

//         if (!found) {
//             // If no properties match the filter, you can handle this here
//             console.log(`No properties found for type: ${type}`);
//         }
//     }

//     toggleRent.addEventListener('click', function () {
//         filterProperties('rent');
//         toggleRent.classList.add('active');
//         toggleSale.classList.remove('active');
//     });

//     toggleSale.addEventListener('click', function () {
//         filterProperties('sale');
//         toggleSale.classList.add('active');
//         toggleRent.classList.remove('active');
//     });

//     // Initial Load - Show Rent Properties
//     filterProperties('rent');
// });



// document.addEventListener("DOMContentLoaded", function () {
//     // Carousel Functionality
//     const carousels = document.querySelectorAll('.carousel');
//     carousels.forEach(carousel => {
//         const additionalImages = carousel.querySelector('.carousel-additional');
//         const items = carousel.querySelectorAll('.carousel-item');
//         let currentIndex = 0;

//         function showSlide(index) {
//             additionalImages.style.transform = `translateX(-${index * 100}%)`;
//         }

//         showSlide(currentIndex);
//         setInterval(() => {
//             currentIndex = (currentIndex + 1) % items.length;
//             showSlide(currentIndex);
//         }, 3000); // Change slide every 3 seconds
//     });

//     // Toggle Buttons Functionality
//     const toggleRent = document.getElementById('toggle-rent');
//     const toggleSale = document.getElementById('toggle-sale');
//     const propertyCards = document.querySelectorAll('.property-card');

//     function filterProperties(type) {
//         propertyCards.forEach(card => {
//             if (card.dataset.type === type || type === 'all') {
//                 card.style.display = 'block';
//             } else {
//                 card.style.display = 'none';
//             }
//         });
//     }

//     toggleRent.addEventListener('click', function () {
//         filterProperties('rent');
//         toggleRent.classList.add('active');
//         toggleSale.classList.remove('active');
//     });

//     toggleSale.addEventListener('click', function () {
//         filterProperties('sale');
//         toggleSale.classList.add('active');
//         toggleRent.classList.remove('active');
//     });

//     // Initial Load - Show Rent Properties
//     filterProperties('rent');
// });

 



document.addEventListener("DOMContentLoaded", function () {
    // Carousel Functionality
    const carousels = document.querySelectorAll('.carousel');
    carousels.forEach(carousel => {
        let items = carousel.querySelectorAll('.carousel-item');
        let currentIndex = 0;

        function showSlide(index) {
            items.forEach((item, i) => {
                item.classList.toggle('active', i === index);
            });
        }

        showSlide(currentIndex);
        setInterval(() => {
            currentIndex = (currentIndex + 1) % items.length;
            showSlide(currentIndex);
        }, 3000); // Change slide every 3 seconds
    });

    // Toggle Buttons Functionality
    const toggleRent = document.getElementById('toggle-rent');
    const toggleSale = document.getElementById('toggle-sale');
    const propertyCards = document.querySelectorAll('.property-card');

    function filterProperties(type) {
        propertyCards.forEach(card => {
            if (card.dataset.type === type || type === 'all') {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    toggleRent.addEventListener('click', function () {
        filterProperties('rent');
        toggleRent.classList.add('active');
        toggleSale.classList.remove('active');
    });

    toggleSale.addEventListener('click', function () {
        filterProperties('sale');
        toggleSale.classList.add('active');
        toggleRent.classList.remove('active');
    });

    // Initial Load - Show Rent Properties
    filterProperties('rent');
});
