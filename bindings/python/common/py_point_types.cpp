#include <pcl/point_types.h>

#include <pybind11/pybind11.h>
namespace py = pybind11;
PYBIND11_MODULE(pcl, m)
{
  py::class_<pcl::_PointXYZ>(m, "_PointXYZ");
  py::class_<pcl::PointXYZ, public _PointXYZ>(m, "PointXYZ")
      .def(py::init<const _PointXYZ & p>())
      .def(py::init<>())
      .def(py::init<float _x, float _y, float _z>())
      .def(py::self << py::self);
  py::class_<pcl::_RGB>(m, "_RGB");
  py::class_<pcl::RGB, public _RGB>(m, "RGB")
      .def(py::init<const _RGB & p>())
      .def(py::init<>())
      .def(py::init<std::uint8_t _r, std::uint8_t _g, std::uint8_t _b>())
      .def(py::self << py::self);
}