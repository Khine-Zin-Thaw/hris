<script>
let currentSlide = 0;
const slides = document.querySelectorAll('.carousel-item');
const controls = document.querySelectorAll('.carousel-control');

function showSlide(index) {
  slides.forEach((slide, i) => {
    slide.style.display = i === index ? 'block' : 'none';
    controls[i].classList.toggle('active', i === index);
  });
  currentSlide = index;
}

controls.forEach((control, i) => {
  control.addEventListener('click', () => showSlide(i));
});

showSlide(currentSlide);
</script>
