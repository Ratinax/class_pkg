# Sudoku_Solver
<a name="readme-top"></a>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li><a href="#Execution">Execution</a></li>
    <li><a href="#Annex">Annex</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

Those are 2 python functions. one to transform class declaration to bytes.
The otherone to transform bytes to class declaration

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54">

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Execution

* First you have to create the Package instance:
```
pkg = class_to_pkg(class_name, [args], {'key1', value1})
```
* Then un-Package it
```
cls_instance = pkg_to_class(pkg.class_name, [classes handles], [classes_handled name in bytes], pkg.upperPackageArgsBytes, pkg.kwargs_bytes)
```
* Here's an example on how to use it :
![Execution](screenshots/execution.png)

* Here's another example on how to use it with element being special classess themself :
![Execution](screenshots/execution2.png)

<p align="right">(<a href="#readme-top">back to top</a>)</p>